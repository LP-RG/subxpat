module abs_diff_i22_o11(a,b,r);
input [10:0] a,b;
output [10:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
