module abs_diff_i7680_o3840(a,b,r);
input [3839:0] a,b;
output [3839:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
