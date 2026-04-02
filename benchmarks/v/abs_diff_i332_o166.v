module abs_diff_i332_o166(a,b,r);
input [165:0] a,b;
output [165:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
