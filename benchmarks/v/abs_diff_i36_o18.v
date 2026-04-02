module abs_diff_i36_o18(a,b,r);
input [17:0] a,b;
output [17:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
