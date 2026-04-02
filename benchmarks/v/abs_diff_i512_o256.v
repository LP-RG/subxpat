module abs_diff_i512_o256(a,b,r);
input [255:0] a,b;
output [255:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
