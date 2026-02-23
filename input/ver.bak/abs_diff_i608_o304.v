module abs_diff_i608_o304(a,b,r);
input [303:0] a,b;
output [303:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
