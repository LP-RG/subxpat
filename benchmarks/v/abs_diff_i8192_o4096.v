module abs_diff_i8192_o4096(a,b,r);
input [4095:0] a,b;
output [4095:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
