module abs_diff_i816_o408(a,b,r);
input [407:0] a,b;
output [407:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
