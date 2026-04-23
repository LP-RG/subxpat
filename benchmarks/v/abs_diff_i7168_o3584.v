module abs_diff_i7168_o3584(a,b,r);
input [3583:0] a,b;
output [3583:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
