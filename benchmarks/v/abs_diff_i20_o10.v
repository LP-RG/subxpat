module abs_diff_i20_o10(a,b,r);
input [9:0] a,b;
output [9:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
