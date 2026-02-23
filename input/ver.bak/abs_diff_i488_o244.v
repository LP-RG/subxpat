module abs_diff_i488_o244(a,b,r);
input [243:0] a,b;
output [243:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
