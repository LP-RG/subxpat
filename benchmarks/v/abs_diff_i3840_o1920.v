module abs_diff_i3840_o1920(a,b,r);
input [1919:0] a,b;
output [1919:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
